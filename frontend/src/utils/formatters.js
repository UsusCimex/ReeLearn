/**
 * Форматирует размер файла в удобочитаемый формат (KB, MB, GB и т.д.)
 * @param {number} bytes - размер файла в байтах
 * @param {number} decimals - количество знаков после запятой (по умолчанию 2)
 * @returns {string} отформатированный размер файла
 */
export const formatFileSize = (bytes, decimals = 2) => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

/**
 * Форматирует длительность в секундах в удобочитаемый формат (mm:ss)
 * @param {number} seconds - длительность в секундах
 * @returns {string} отформатированная длительность
 */
export const formatDuration = (seconds) => {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
};

/**
 * Сокращает строку, если она превышает указанную длину
 * @param {string} str - исходная строка
 * @param {number} maxLength - максимальная длина (по умолчанию 100)
 * @returns {string} сокращенная строка с многоточием при необходимости
 */
export const truncateString = (str, maxLength = 100) => {
  if (!str || str.length <= maxLength) return str;
  return `${str.substring(0, maxLength)}...`;
};
