import { useContext } from "react";
import { LanguageContext } from "../LanguageContext";
import { translations } from "../i18n";

export const useTranslation = () => {
  const { language } = useContext(LanguageContext);
  const t = (key) => translations[language][key] || key;
  return { t, language };
};
