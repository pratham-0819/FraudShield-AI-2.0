from datetime import datetime, timedelta
from math import asin, cos, radians, sin, sqrt

from sqlalchemy.orm import Session

from ..database.models import GeoEvent, GeoProfile


CITY_COORDINATES = {
    "mumbai": (19.0760, 72.8777),
    "navi mumbai": (19.0330, 73.0297),
    "thane": (19.2183, 72.9781),
    "delhi": (28.6139, 77.2090),
    "new delhi": (28.6139, 77.2090),
    "bangalore": (12.9716, 77.5946),
    "bengaluru": (12.9716, 77.5946),
    "hyderabad": (17.3850, 78.4867),
    "chennai": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639),
    "pune": (18.5204, 73.8567),
    "ahmedabad": (23.0225, 72.5714),
    "dubai": (25.2048, 55.2708),
    "singapore": (1.3521, 103.8198),
    "london": (51.5072, -0.1276),
    "new york": (40.7128, -74.0060),
}

TRUSTED_RADIUS_KM = 75
SUSPICIOUS_RADIUS_KM = 250
IMPOSSIBLE_TRAVEL_SPEED_KMH = 900


class GeoEngine:
    def normalize_location(self, location):
        return location.strip().lower()

    def resolve_coordinates(self, location):
        return CITY_COORDINATES.get(self.normalize_location(location))

    def haversine_km(self, origin, destination):
        lat1, lon1 = origin
        lat2, lon2 = destination

        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        a = (
            sin(delta_lat / 2) ** 2
            + cos(radians(lat1)) * cos(radians(lat2)) * sin(delta_lon / 2) ** 2
        )
        return 6371 * 2 * asin(sqrt(a))

    def build_event_time(self, latest_event, time_text):
        try:
            parsed_clock = datetime.strptime(time_text, "%H:%M").time()
        except ValueError:
            parsed_clock = datetime.strptime("12:00", "%H:%M").time()

        base_date = latest_event.event_time.date() if latest_event else datetime.utcnow().date()
        event_time = datetime.combine(base_date, parsed_clock)

        if latest_event and event_time <= latest_event.event_time:
            event_time = event_time + timedelta(days=1)

        return event_time

    def assess_location(self, db: Session, sender, transaction_location, time_text):
        normalized_location = self.normalize_location(transaction_location)
        coordinates = self.resolve_coordinates(transaction_location)

        profiles = (
            db.query(GeoProfile)
            .filter(GeoProfile.sender == sender)
            .order_by(GeoProfile.seen_count.desc(), GeoProfile.last_seen_at.desc())
            .all()
        )
        trusted_profiles = [profile for profile in profiles if profile.seen_count >= 2]
        latest_event = (
            db.query(GeoEvent)
            .filter(GeoEvent.sender == sender)
            .order_by(GeoEvent.event_time.desc())
            .first()
        )
        event_time = self.build_event_time(latest_event, time_text)

        geo_flag = "LOW_RISK"
        explanation = "Known or nearby location."

        if trusted_profiles:
            if coordinates and any(
                profile.latitude is not None
                and profile.longitude is not None
                and self.haversine_km(
                    coordinates,
                    (profile.latitude, profile.longitude),
                ) <= TRUSTED_RADIUS_KM
                for profile in trusted_profiles
            ):
                geo_flag = "LOW_RISK"
                explanation = "Location is near a trusted user hub."
            elif any(
                self.normalize_location(profile.location) == normalized_location
                for profile in trusted_profiles
            ):
                geo_flag = "LOW_RISK"
                explanation = "Exact trusted location match."
            elif coordinates and any(
                profile.latitude is not None
                and profile.longitude is not None
                and self.haversine_km(
                    coordinates,
                    (profile.latitude, profile.longitude),
                ) <= SUSPICIOUS_RADIUS_KM
                for profile in trusted_profiles
            ):
                geo_flag = "MEDIUM_RISK"
                explanation = "Location is outside the normal hub but still nearby."
            else:
                geo_flag = "HIGH_RISK"
                explanation = "Location is far from the user's trusted history."
        elif profiles:
            if any(
                self.normalize_location(profile.location) == normalized_location
                for profile in profiles
            ):
                geo_flag = "LOW_RISK"
                explanation = "Location matches prior history."
            else:
                geo_flag = "MEDIUM_RISK"
                explanation = "New location for user with limited history."
        else:
            explanation = "First observed location for this sender."

        impossible_travel = False
        travel_speed = None
        if (
            latest_event
            and coordinates
            and latest_event.latitude is not None
            and latest_event.longitude is not None
        ):
            previous_coordinates = (latest_event.latitude, latest_event.longitude)
            previous_time = latest_event.event_time
            hours_between = (event_time - previous_time).total_seconds() / 3600
            if hours_between > 0:
                distance_km = self.haversine_km(previous_coordinates, coordinates)
                travel_speed = distance_km / hours_between
                if distance_km >= 300 and hours_between < 0.5:
                    impossible_travel = True
                    geo_flag = "HIGH_RISK"
                    explanation = (
                        f"Rapid long-distance location jump detected "
                        f"at {travel_speed:.0f} km/h."
                    )
                else:
                    if travel_speed > IMPOSSIBLE_TRAVEL_SPEED_KMH:
                        impossible_travel = True
                        geo_flag = "HIGH_RISK"
                        explanation = (
                            f"Impossible travel detected at {travel_speed:.0f} km/h."
                        )

        profile = next(
            (
                item
                for item in profiles
                if self.normalize_location(item.location) == normalized_location
            ),
            None,
        )

        if profile:
            profile.seen_count += 1
            profile.last_seen_at = event_time
            if coordinates:
                profile.latitude, profile.longitude = coordinates
        else:
            db.add(
                GeoProfile(
                    sender=sender,
                    location=transaction_location,
                    latitude=coordinates[0] if coordinates else None,
                    longitude=coordinates[1] if coordinates else None,
                    seen_count=1,
                    last_seen_at=event_time,
                )
            )

        db.add(
            GeoEvent(
                sender=sender,
                location=transaction_location,
                latitude=coordinates[0] if coordinates else None,
                longitude=coordinates[1] if coordinates else None,
                event_time=event_time,
            )
        )

        return {
            "flag": geo_flag,
            "explanation": explanation,
            "impossible_travel": impossible_travel,
            "travel_speed_kmh": round(travel_speed, 1) if travel_speed else None,
            "trusted_locations": len(trusted_profiles),
        }
