import moment from 'moment-jalaali';

/**
 * Convert a date string to Jalali (Persian) calendar with Tehran timezone
 * @param {string} dateString - ISO date string
 * @returns {string} - Formatted Jalali date and time in Tehran timezone (English numbers)
 */
export const formatDateTimeToJalaliTehran = (dateString) => {
  if (!dateString) return 'N/A';
  
  try {
    // Parse the date string
    // If it has 'Z' or timezone offset, parse as UTC
    // Otherwise parse as local time
    let date;
    if (dateString.includes('Z') || dateString.match(/[+-]\d{2}:\d{2}$/)) {
      // ISO string with timezone - parse as UTC
      date = moment.utc(dateString);
    } else {
      // No timezone info - assume it's already UTC (from backend)
      date = moment.utc(dateString);
    }
    
    // Convert to Tehran timezone (UTC+3:30)
    // utcOffset with positive value (210 minutes) means ahead of UTC
    const tehranDate = date.utcOffset(210); // 3.5 hours = 210 minutes
    
    // Format to Jalali calendar with English numbers
    // Format: YYYY/MM/DD HH:mm:ss
    const jalaliDate = tehranDate.format('jYYYY/jMM/jDD');
    const time = tehranDate.format('HH:mm:ss');
    
    return `${jalaliDate} ${time}`;
  } catch (error) {
    return 'N/A';
  }
};

/**
 * Format only the time portion in Tehran timezone (Jalali calendar context)
 * @param {string} dateString - ISO date string
 * @returns {string} - Formatted time in Tehran timezone (HH:MM:SS)
 */
export const formatTimeToTehran = (dateString) => {
  if (!dateString) return 'N/A';
  
  try {
    // Parse the date string
    // If it has 'Z' or timezone offset, parse as UTC
    // Otherwise parse as UTC (from backend)
    let date;
    if (dateString.includes('Z') || dateString.match(/[+-]\d{2}:\d{2}$/)) {
      date = moment.utc(dateString);
    } else {
      date = moment.utc(dateString);
    }
    
    // Convert to Tehran timezone (UTC+3:30)
    const tehranDate = date.utcOffset(210); // 3.5 hours = 210 minutes
    return tehranDate.format('HH:mm:ss');
  } catch (error) {
    return 'N/A';
  }
};

/**
 * Format date and time, with time in Tehran timezone (backward compatibility)
 * @param {string} dateString - ISO date string
 * @returns {string} - Formatted Jalali date with Tehran time
 */
export const formatDateTimeWithTehranTime = (dateString) => {
  return formatDateTimeToJalaliTehran(dateString);
};

