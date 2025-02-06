import React, { createContext, useState } from "react";

export const LanguageContext = createContext({
  language: "ru",
  setLanguage: () => {}
});

export const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState("ru");
  return (
    <LanguageContext.Provider value={{ language, setLanguage }}>
      {children}
    </LanguageContext.Provider>
  );
};
