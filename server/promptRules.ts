/**
 * Strict prompt rules for laboratory instrument measurement methods
 * DeepSeek Integration with Russian query support
 */

/**
 * Check if query contains Cyrillic characters (Russian text)
 */
export function isRussian(text: string): boolean {
  const cyrillicPattern = /[\u0400-\u04FF]/;
  return cyrillicPattern.test(text);
}

/**
 * Check if instrument is mentioned in the query
 * More lenient - checks for general lab equipment terms
 */
export function hasInstrumentMention(text: string): boolean {
  const lowerText = text.toLowerCase();
  
  // Broader keywords including test equipment
  const keywords = [
    // Spectrophotometers
    'спектрофотометр', 'spectrophotometer',
    // Chromatographs  
    'хроматограф', 'chromatograph', 'жх', 'вэжх', 'hplc', 'uhplc',
    // pH meters
    'ph-метр', 'pH-метр', 'ph-meter', 'pH-meter', 'pH meter', 'измеритель ph',
    // Balances
    'весы', 'balance', 'scale', 'аналитические весы',
    // Centrifuges
    'центрифуга', 'centrifuge', 'микроцентрифуга',
    // Microscopes
    'микроскоп', 'microscope',
    // Thermocyclers
    'термоциклер', 'thermocycler', 'пцр', 'pcr',
    // Spectrometers
    'спектрометр', 'spectrometer', 'масс-спектрометр', 'mass spectrometer',
    // Test machines / equipment
    'тест-машина', 'тестмашина', 'тест машина', 'test-machine', 'test machine', 'tester', 'тестер',
    'испытательная машина', 'испытатель', 'testing machine', 'test equipment',
    // Generic terms
    'прибор', 'instrument', 'аппарат', 'device', 'оборудование', 'equipment',
    'анализатор', 'analyzer', 'детектор', 'detector',
    // Method-related (to catch methodology questions)
    'методика', 'method', 'метод', 'калибровка', 'calibration', 'измерение', 'measurement',
  ];
  
  return keywords.some(k => lowerText.includes(k.toLowerCase()));
}

/**
 * Extract instrument names and models from query
 * Normalizes "тест-машина" and "тестмашина" to same entity
 */
export function extractInstrumentNames(text: string): string[] {
  const instruments = new Set<string>();
  const lowerText = text.toLowerCase();
  
  // Normalize: treat "тест-машина", "тестмашина", "тест машина" as same
  if (lowerText.includes('тест-машина') || lowerText.includes('тестмашина') || 
      lowerText.includes('тест машина') || lowerText.includes('test-machine') ||
      lowerText.includes('test machine') || lowerText.includes('tester') ||
      lowerText.includes('тестер') || lowerText.includes('испытательная машина')) {
    instruments.add('тест-машина');
  }
  
  const patterns = [
    /спектрофотометр\s+([a-zA-Z0-9\-]+)/gi,
    /хроматограф\s+([a-zA-Z0-9\-]+)/gi,
    /ph-?метр\s+([a-zA-Z0-9\-]+)/gi,
    /весы\s+([a-zA-Z0-9\-]+)/gi,
    /центрифуга\s+([a-zA-Z0-9\-]+)/gi,
    /микроскоп\s+([a-zA-Z0-9\-]+)/gi,
    /термоциклер\s+([a-zA-Z0-9\-]+)/gi,
    /спектрометр\s+([a-zA-Z0-9\-]+)/gi,
    /тест-?машина\s+([a-zA-Z0-9\-]+)/gi,
    /spectrophotometer\s+([a-zA-Z0-9\-]+)/gi,
    /chromatograph\s+([a-zA-Z0-9\-]+)/gi,
    /ph-?meter\s+([a-zA-Z0-9\-]+)/gi,
    /balance\s+([a-zA-Z0-9\-]+)/gi,
    /centrifuge\s+([a-zA-Z0-9\-]+)/gi,
    /tester\s+([a-zA-Z0-9\-]+)/gi,
  ];
  
  for (const pattern of patterns) {
    let match: RegExpExecArray | null;
    while ((match = pattern.exec(text)) !== null) {
      if (match[1]) {
        instruments.add(match[1].trim());
      }
    }
  }
  
  // Also check for standalone instrument type mentions
  const instrumentTypes = [
    'спектрофотометр', 'spectrophotometer',
    'хроматограф', 'chromatograph',
    'ph-метр', 'pH-метр', 'pH-meter', 'ph-meter',
    'весы', 'balance', 'scale',
    'центрифуга', 'centrifuge',
    'микроскоп', 'microscope',
    'термоциклер', 'thermocycler',
    'спектрометр', 'spectrometer',
    'тест-машина', 'test-machine', 'tester',
  ];
  
  for (const type of instrumentTypes) {
    if (lowerText.includes(type.toLowerCase())) {
      instruments.add(type);
    }
  }
  
  return Array.from(instruments);
}

/**
 * Check if multiple instrument models are detected
 */
export function hasMultipleModels(instruments: string[]): boolean {
  return instruments.length > 1;
}

/**
 * Build clarification prompt when instrument is not mentioned
 * [DISABLED] Decided to allow general questions to proceed to RAG.
 */
export function buildClarificationPrompt(): string {
  return "Пожалуйста, уточните ваш вопрос.";
}

/**
 * Build model clarification prompt when multiple models detected
 * Rule 7: If multiple models are found – ask the user to clarify the model.
 */
export function buildModelClarificationPrompt(models: string[]): string {
  return `Обнаружено несколько моделей приборов: ${models.join(', ')}. Пожалуйста, уточните, для какой модели нужна методика.`;
}

/**
 * Build strict formatted response for instrument queries
 * Rule 3: Build answer with exact structure - improved to be selective
 */
export function buildInstrumentResponse(
  instrument: string,
  calibration: string | null,
  methodology: string | null,
  fromInternet: boolean,
  notInDatabase: boolean,
  userQuery: string = ""
): string {
  const lowerQuery = userQuery.toLowerCase();
  const wantsCalibration = ['калибровк', 'calibrate', 'настройк'].some(w => lowerQuery.includes(w)) || !lowerQuery.includes('измерен');
  const wantsMethodology = ['измерен', 'метод', 'инструкц', 'как работа', 'measure', 'method', 'instruction'].some(w => lowerQuery.includes(w)) || !lowerQuery.includes('калибровк');

  let response = `Прибор: ${instrument}\n\n`;
  
  if (fromInternet) {
    response += `⚠️ Информация получена из внешних источников.\n\n`;
  }
  
  if (wantsCalibration || !userQuery) {
    response += `### Калибровка:\n${calibration || 'Информация о калибровке для данной модели в базе отсутствует'}\n\n`;
  }
  
  if (wantsMethodology || !userQuery) {
    response += `### Методика измерения:\n${methodology || 'Информация о методике измерения для данной модели в базе отсутствует'}\n\n`;
  }
  
  if (notInDatabase && !fromInternet) {
    response += `⚠️ Детальная информация по вашему запросу отсутствует в нашей базе знаний. Я привел общие данные, если они были найдены.\n`;
  }
  
  return response;
}
