import { timedEventManager } from "#app/global-event-manager";
import { namespaceMap } from "#app/i18n-namespace-map";
import { SUPPORTED_LANGUAGES } from "#system/supported-languages";
import { getCachedUrl } from "#utils/fetch-utils";
import { toKebabCase } from "#utils/strings";
import i18next from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import HttpBackend from "i18next-http-backend";
import { KoreanPostpositionProcessor } from "i18next-korean-postposition-processor";

// #region Interfaces/Types

interface LoadingFontFaceProperty {
  face: FontFace;
  extraOptions?: { [key: string]: any };
  only?: string[];
}

// #endregion Interfaces/Types

// #region Constants

// 블서로그: 한국어만 써서 글꼴은 index.html 의 갈무리11 하나로 충분해요
const fonts: LoadingFontFaceProperty[] = [];

// #endregion Constants

// #region Functions

async function initFonts(language: string | undefined) {
  const results = await Promise.allSettled(
    fonts
      .filter(font => !font.only || font.only.some(exclude => language?.indexOf(exclude) === 0))
      .map(font => Object.assign(font.face, font.extraOptions ?? {}).load()),
  );
  for (const result of results) {
    if (result.status === "fulfilled") {
      document.fonts?.add(result.value);
    } else {
      console.error(result.reason);
    }
  }
}

/**
 * I18n money formatter with. (useful for BBCode coloring of text) \
 * _If you don't want the BBCode tag applied, just use 'number' formatter_
 * @example Input: `{{myMoneyValue, money}}`
 *          Output: `@[MONEY]{₽100,000,000}`
 * @param amount the money amount
 * @returns a money formatted string
 */
function i18nMoneyFormatter(amount: any): string {
  if (Number.isNaN(Number(amount))) {
    console.warn(`i18nMoneyFormatter: value "${amount}" is not a number!`);
  }

  return `@[MONEY]{${i18next.t("common:money", { amount })}}`;
}

// #endregion Functions

// populated during post-processing in `plugins/vite/namespaces-i18n-plugin.ts`
const nsEn: string[] = [];

// #region Init

/*
 * i18next is a localization library for maintaining and using translation resources.
 *
 * Q: How do I add a new language?
 * A: To add a new language, create a new folder in the locales directory with the language code.
 *    Each language folder should contain a file for each namespace (e.g. `menu.json`) with the translations.
 *    Don't forget to add an entry to `SUPPORTED_LANGUAGE_ENTRIES` in `src/system/supported-languages.ts`
 *
 * Q: How do I add a new namespace?
 * A: To add a new namespace, create a new file .json in each language folder with the translations.
 *    The expected format for the file-name is kebab-case (see https://developer.mozilla.org/en-US/docs/Glossary/Kebab_case).
 *    If you want the namespace name to be different from the file name, configure it in `src/i18n-namespace-map.ts`.
 */

await i18next
  .use(HttpBackend)
  .use(LanguageDetector)
  .use(new KoreanPostpositionProcessor())
  .init(
    {
      // 블서로그: 한국어만
      lng: "ko",
      fallbackLng: "ko",
      supportedLngs: SUPPORTED_LANGUAGES,
      backend: {
        loadPath(lng: string, [ns]: string[]) {
          // Use namespace maps where required
          let fileName: string;
          if (namespaceMap[ns]) {
            fileName = namespaceMap[ns];
          } else if (ns.startsWith("mysteryEncounters/")) {
            fileName = toKebabCase(ns + "-dialogue"); // mystery-encounters/a-trainers-test-dialogue
          } else {
            fileName = toKebabCase(ns);
          }
          // ex: "./locales/en/move-anims?t=1234567890"
          return getCachedUrl(`./locales/${lng}/${fileName}.json`);
        },
      },
      defaultNS: "menu",
      detection: {
        lookupLocalStorage: "prLang",
        caches: [],
        order: [],
      },
      ns: nsEn,
      debug: import.meta.env.VITE_I18N_DEBUG === "1",
      interpolation: {
        // Phaser is unable to parse the HTML escape codes produced by i18next, so turning this on results in codes like
        // &amp; being displayed verbatim on screen.
        // We use i18next solely for localizing values inside code anyways, so the risk of XSS from user input is virtually nonexistent.
        escapeValue: false,
        // While using the `$t()` string syntax can allow nested locale keys to lazily look up interpolated text in the current chosen language,
        // the fact that we reload the page after a language change renders this entirely moot - any nested lookups will be re-evaluated anyway.
        // Moreover, this means of passing nested keys lacks the type-safety of calling `i18next.t` directly,
        // which will be important once we get said strong typing set up correctly.
        skipOnVariables: true,
      },
      postProcess: ["korean-postposition"],
    },
    async () => {
      i18next.services.formatter?.add("money", i18nMoneyFormatter);
      await initFonts(localStorage.getItem("prLang") ?? undefined);
    },
  );

// #endregion Init

// #region Event Proxy

if (timedEventManager.hasEventTextReplacement()) {
  console.warn("Event text replacements are active.");
  i18next.t = new Proxy(i18next.t.bind(i18next), {
    apply(target, _, args: [key: string, options?: any]) {
      const key = timedEventManager.getEventTextReplacement(args[0]);
      if (args[0] !== key) {
        console.debug(`Replacing i18n key "${args[0]}" with "${key}"`);
        args[0] = key;
      }
      return target(...args);
    },
  });
}

// #endregion Event Proxy
