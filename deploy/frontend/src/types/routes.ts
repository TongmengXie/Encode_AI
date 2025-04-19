/**
 * Represents a transportation route option
 */
export interface RouteOption {
  mode: string; // 'flight', 'train', 'bus', 'car', etc.
  duration: string;
  cost: string;
  carbon_footprint: string;
  comfort_level: string;
  pros: string[];
  cons: string[];
}

/**
 * Response from the route generation API
 */
export interface RouteGenerationResponse {
  success: boolean;
  routes: RouteOption[];
  origin: string;
  destination: string;
  message?: string;
  traceback?: string;
}

/**
 * Response from the route selection API
 */
export interface RouteSelectionResponse {
  success: boolean;
  message: string;
  selected_route: RouteOption;
} 