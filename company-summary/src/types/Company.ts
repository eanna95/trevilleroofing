export interface Company {
  company_name: string;
  state: string;
  investment_grade: string;
  investment_grade_citations: string[];
  est_annual_revenue: string;
  est_annual_revenue_citations: string[];
  est_yoy_growth: string;
  est_yoy_growth_citations: string[];
  pe_backed: string;
  pe_backed_citations: string[];
  can_accommodate_allocation: string;
  can_accommodate_allocation_citations: string[];
  good_reputation: string;
  good_reputation_citations: string[];
  phone_numbers?: string[];
}

export interface ColumnConfig {
  key: keyof Company;
  label: string;
  type: 'definition' | 'metric';
  visible: boolean;
  order: number;
}

export const columnConfigs: ColumnConfig[] = [
  { key: 'company_name', label: 'Company Name', type: 'definition', visible: true, order: 0 },
  { key: 'state', label: 'State', type: 'definition', visible: true, order: 1 },
  { key: 'investment_grade', label: 'Investment Grade', type: 'metric', visible: true, order: 2 },
  { key: 'est_annual_revenue', label: 'Estimated annual revenue ($)', type: 'metric', visible: true, order: 3 },
  { key: 'est_yoy_growth', label: 'Estimated YoY growth (%)', type: 'metric', visible: true, order: 4 },
  { key: 'pe_backed', label: 'PE-backed (y/n)', type: 'metric', visible: true, order: 5 },
  { key: 'can_accommodate_allocation', label: 'Able to accommodate $10M capital allocation (y/n)', type: 'metric', visible: true, order: 6 },
  { key: 'good_reputation', label: 'Good Reputation', type: 'metric', visible: true, order: 7 },
];