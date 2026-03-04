import {
  TranslateClient,
  TranslateTextCommand,
} from "@aws-sdk/client-translate";
import {
  ComprehendClient,
  DetectDominantLanguageCommand,
} from "@aws-sdk/client-comprehend";

const translateClient = new TranslateClient({
  region: process.env.AWS_REGION || "ap-south-1",
});
const comprehendClient = new ComprehendClient({
  region: process.env.AWS_REGION || "ap-south-1",
});

// Supported Indian languages in AWS Translate
export const SUPPORTED_LANGUAGES = {
  hi: "Hindi",
  bn: "Bengali",
  ta: "Tamil",
  te: "Telugu",
  mr: "Marathi",
  gu: "Gujarati",
  kn: "Kannada",
  ml: "Malayalam",
  pa: "Punjabi",
  ur: "Urdu",
  en: "English",
};

/**
 * Detect the language of the input text using AWS Comprehend
 */
export async function detectLanguage(text: string): Promise<string> {
  try {
    const command = new DetectDominantLanguageCommand({ Text: text });
    const response = await comprehendClient.send(command);

    if (response.Languages && response.Languages.length > 0) {
      const detectedLang = response.Languages[0].LanguageCode || "en";
      return detectedLang;
    }

    return "en"; // Default to English
  } catch (error) {
    console.error("Language detection error:", error);
    // Fallback: Simple heuristic detection
    return detectLanguageHeuristic(text);
  }
}

/**
 * Simple heuristic language detection for Indian languages
 * Uses Unicode ranges for different scripts
 */
function detectLanguageHeuristic(text: string): string {
  // Hindi (Devanagari script)
  if (/[\u0900-\u097F]/.test(text)) return "hi";

  // Bengali
  if (/[\u0980-\u09FF]/.test(text)) return "bn";

  // Tamil
  if (/[\u0B80-\u0BFF]/.test(text)) return "ta";

  // Telugu
  if (/[\u0C00-\u0C7F]/.test(text)) return "te";

  // Gujarati
  if (/[\u0A80-\u0AFF]/.test(text)) return "gu";

  // Kannada
  if (/[\u0C80-\u0CFF]/.test(text)) return "kn";

  // Malayalam
  if (/[\u0D00-\u0D7F]/.test(text)) return "ml";

  // Punjabi (Gurmukhi)
  if (/[\u0A00-\u0A7F]/.test(text)) return "pa";

  // Urdu (Arabic script)
  if (/[\u0600-\u06FF]/.test(text)) return "ur";

  return "en"; // Default to English
}

/**
 * Translate text from source language to target language using AWS Translate
 */
export async function translateText(
  text: string,
  sourceLanguage: string,
  targetLanguage: string,
): Promise<string> {
  try {
    // If source and target are the same, return original text
    if (sourceLanguage === targetLanguage) {
      return text;
    }

    // Check if languages are supported
    if (
      !SUPPORTED_LANGUAGES[sourceLanguage as keyof typeof SUPPORTED_LANGUAGES]
    ) {
      console.warn(
        `Source language ${sourceLanguage} not supported, using English`,
      );
      sourceLanguage = "en";
    }

    if (
      !SUPPORTED_LANGUAGES[targetLanguage as keyof typeof SUPPORTED_LANGUAGES]
    ) {
      console.warn(
        `Target language ${targetLanguage} not supported, using English`,
      );
      targetLanguage = "en";
    }

    const command = new TranslateTextCommand({
      Text: text,
      SourceLanguageCode: sourceLanguage,
      TargetLanguageCode: targetLanguage,
    });

    const response = await translateClient.send(command);
    return response.TranslatedText || text;
  } catch (error) {
    console.error("Translation error:", error);
    return text; // Return original text on error
  }
}

/**
 * Translate to English (for processing)
 * Returns both translated text and detected language
 */
export async function translateToEnglish(text: string): Promise<{
  translatedText: string;
  detectedLanguage: string;
}> {
  const detectedLanguage = await detectLanguage(text);

  if (detectedLanguage === "en") {
    return { translatedText: text, detectedLanguage };
  }

  const translatedText = await translateText(text, detectedLanguage, "en");
  return { translatedText, detectedLanguage };
}

/**
 * Translate from English to target language
 */
export async function translateFromEnglish(
  text: string,
  targetLanguage: string,
): Promise<string> {
  if (targetLanguage === "en") {
    return text;
  }

  return await translateText(text, "en", targetLanguage);
}

/**
 * Get list of supported languages
 */
export function getSupportedLanguages(): typeof SUPPORTED_LANGUAGES {
  return SUPPORTED_LANGUAGES;
}

/**
 * Check if a language is supported
 */
export function isLanguageSupported(languageCode: string): boolean {
  return languageCode in SUPPORTED_LANGUAGES;
}

/**
 * Batch translate multiple texts (for optimization)
 */
export async function batchTranslate(
  texts: string[],
  sourceLanguage: string,
  targetLanguage: string,
): Promise<string[]> {
  // AWS Translate doesn't have native batch API, so we process sequentially
  // In production, consider using Promise.all for parallel processing
  const results: string[] = [];

  for (const text of texts) {
    const translated = await translateText(
      text,
      sourceLanguage,
      targetLanguage,
    );
    results.push(translated);
  }

  return results;
}
