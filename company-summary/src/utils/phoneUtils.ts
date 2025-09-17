/**
 * Formats a phone number to (area code) ***-**** format
 * @param phoneNumber - Raw phone number string
 * @returns Formatted phone number string
 */
export function formatPhoneNumber(phoneNumber: string): string {
  // Remove all non-digit characters
  const digits = phoneNumber.replace(/\D/g, '');

  // Handle different phone number lengths
  if (digits.length === 10) {
    // Format: (XXX) XXX-XXXX
    return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
  } else if (digits.length === 11 && digits.startsWith('1')) {
    // Remove leading 1 and format
    const cleanDigits = digits.slice(1);
    return `(${cleanDigits.slice(0, 3)}) ${cleanDigits.slice(3, 6)}-${cleanDigits.slice(6)}`;
  } else if (digits.length === 7) {
    // Local number without area code: XXX-XXXX
    return `${digits.slice(0, 3)}-${digits.slice(3)}`;
  }

  // Return original if it doesn't match expected patterns
  return phoneNumber;
}

/**
 * Parses and formats phone numbers from a JSON array string
 * @param phoneNumbersJson - JSON string containing array of phone numbers
 * @returns Array of formatted phone numbers
 */
export function parseAndFormatPhoneNumbers(phoneNumbersJson: string): string[] {
  try {
    const phoneNumbers = JSON.parse(phoneNumbersJson);
    if (Array.isArray(phoneNumbers)) {
      return phoneNumbers.map(formatPhoneNumber);
    }
    return [];
  } catch {
    // If parsing fails, return empty array
    return [];
  }
}

/**
 * Formats multiple phone numbers for display
 * @param phoneNumbers - Array of phone numbers
 * @returns Formatted string with phone numbers separated by commas
 */
export function formatPhoneNumbersForDisplay(phoneNumbers: string[]): string {
  if (!phoneNumbers || phoneNumbers.length === 0) {
    return '';
  }
  return phoneNumbers.join(', ');
}