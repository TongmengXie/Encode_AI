export interface SurveyFormData {
  real_name: string;
  age_group: string;
  gender: string;
  nationality: string;
  preferred_residence?: string;
  cultural_symbol?: string;
  bucket_list?: string;
  healthcare_expectations?: string;
  travel_budget: string;
  currency_preferences?: string;
  insurance_type?: string;
  past_insurance_issues?: string;
  travel_season: string;
  stay_duration?: string;
  interests: string;
  personality_type?: string;
  communication_style?: string;
  travel_style: string;
  accommodation_preference: string;
}

export interface SurveySuccessProps {
  onReturnHome: () => void;
}

export interface SurveyFormProps {
  onSubmit: (values: SurveyFormData) => void;
  isSubmitting: boolean;
} 