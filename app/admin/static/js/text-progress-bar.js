/**
 * Функция создания и управления текстовым прогресс-баром
 * Отображает ASCII прогресс-бар, аналогичный тому, что выводится в терминале
 */

class TextProgressBar {
    constructor(element, options = {}) {
        this.element = element;
        this.options = Object.assign({
            barLength: 40,
            barChar: '#',
            emptyChar: '-',
            showPercentage: true,
            showValues: true,
            wrapperClass: 'text-progress-wrapper',
            barClass: 'text-progress-bar',
            valueClass: 'text-progress-value',
            additionalInfoClass: 'text-progress-info'
        }, options);
        
        this.progress = 0;
        this.total = 100;
        this.current = 0;
        this.additionalInfo = '';
        
        this.init();
    }
    
    init() {
        // Создаем обертку с монопространственным шрифтом
        this.element.classList.add(this.options.wrapperClass);
        this.element.style.fontFamily = 'monospace';
        this.element.style.whiteSpace = 'pre';
        this.element.style.overflowX = 'auto';
        
        // Создаем начальный прогресс-бар
        this.render();
    }
    
    update(current, total, additionalInfo = '') {
        this.current = current;
        this.total = total;
        this.progress = (total > 0) ? (current / total) : 0;
        this.additionalInfo = additionalInfo;
        this.render();
    }
    
    render() {
        const { barLength, barChar, emptyChar, showPercentage, showValues } = this.options;
        
        // Рассчитываем заполненную часть
        let filledLength = Math.floor(barLength * this.progress);
        
        // Добавляем минимум 1 символ, если есть прогресс, но он меньше 1 символа
        if (this.progress > 0 && filledLength === 0) {
            filledLength = 1;
        }
        
        const emptyLength = barLength - filledLength;
        
        // Создаем строку прогресс-бара
        const bar = barChar.repeat(filledLength) + emptyChar.repeat(emptyLength);
        const percentage = (this.progress * 100).toFixed(1) + '%';
        
        // Формируем полную строку
        let barText = `[${bar}]`;
        
        if (showPercentage) {
            barText += ` ${percentage}`;
        }
        
        if (showValues) {
            barText += ` (${this.current}/${this.total})`;
        }
        
        if (this.additionalInfo) {
            barText += ` | ${this.additionalInfo}`;
        }
        
        // Обновляем содержимое элемента
        this.element.textContent = barText;
    }
}

// Экспортируем класс для использования в других модулях
window.TextProgressBar = TextProgressBar;