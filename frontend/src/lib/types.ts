export interface SystemMessage {
  agent_name: string;
  instructions: string;
  steps: string[];
  output: string;
  status_code: number;
}

export interface Message {
  role: string;
  prompt?: string;
  data?: SystemMessage[];
}
