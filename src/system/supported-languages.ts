export type SupportedLanguageEntry = {
  readonly [key: string]: { readonly label: string; readonly hasAllLocalizedImages: boolean };
};

// 블서로그는 한국어만 써요
export const SUPPORTED_LANGUAGE_ENTRIES = {
  ko: {
    label: "한국어", // Korean
    hasAllLocalizedImages: true,
  },
} as const satisfies SupportedLanguageEntry;

export const SUPPORTED_LANGUAGES = Object.keys(SUPPORTED_LANGUAGE_ENTRIES) as SupportedLanguage[];

export type SupportedLanguage = keyof typeof SUPPORTED_LANGUAGE_ENTRIES;
