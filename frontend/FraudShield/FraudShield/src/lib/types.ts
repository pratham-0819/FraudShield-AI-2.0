export type SimulationRequest = {
  sender: string;
  receiver: string;
  amount: number;
  age: number;
  location: string;
  device: string;
  time: string;
  scenario: string;
  policy_strictness: number;
};

export type SimulationResponse = {
  risk_score: number;
  action: string;
  fraud_probability: number;
  model_probability?: number;
  xai: Record<string, string>;
  model_explanation?: {
    base_probability: number;
    top_risk_drivers: Array<{
      feature: string;
      impact: number;
      actual_value: number;
      reference_value: number;
      direction: string;
    }>;
    top_protective_factors: Array<{
      feature: string;
      impact: number;
      actual_value: number;
      reference_value: number;
      direction: string;
    }>;
    narrative: string;
  };
  advanced_explanation: Record<string, number>;
  flags: {
    behavior: string;
    graph: string;
    geo: string;
    velocity: string;
  };
  geo_details?: {
    flag: string;
    explanation: string;
    impossible_travel: boolean;
    travel_speed_kmh: number | null;
    trusted_locations: number;
  };
  risk_breakdown: Record<string, number>;
  summary: string;
};
