/**
 * Set a cookie
 */
export const setCookie = (name, value, daysToExpire) => {
  let expires = "";
  if (daysToExpire) {
    const date = new Date();
    date.setTime(date.getTime() + daysToExpire * 24 * 60 * 60 * 1000);
    expires = `; expires=' + ${date.toUTCString()}`;
  }
  document.cookie = `${name}=${value}${expires}; path=/`;
};

/**
 * Get a cookie by name
 */
export const getCookie = (name) => {
  const cookieName = `${name}=`;
  const cookieArray = document.cookie.split(";");
  for (let i = 0; i < cookieArray.length; i += 1) {
    const cookie = cookieArray[i].trim();
    if (cookie.indexOf(cookieName) === 0) {
      return cookie.substring(cookieName.length, cookie.length);
    }
  }
  return null;
};
