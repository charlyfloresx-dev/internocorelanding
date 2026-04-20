import { Directive, ElementRef, HostListener, Input, Output, EventEmitter, inject } from '@angular/core';

@Directive({
  selector: '[appExcelNav]',
  standalone: true
})
export class ExcelNavDirective {
  @Input() appExcelNavRows = 0;
  @Input() appExcelNavCols = 0;
  @Output() addRow = new EventEmitter<void>();
  @Output() pasteData = new EventEmitter<string[][]>();

  private el = inject(ElementRef);

  @HostListener('keydown', ['$event'])
  handleKeyDown(event: KeyboardEvent) {
    const target = event.target as HTMLElement;
    const row = parseInt(target.getAttribute('data-row') || '-1');
    const col = parseInt(target.getAttribute('data-col') || '-1');

    if (row === -1 || col === -1) return;

    switch (event.key) {
      case 'ArrowUp':
        this.moveFocus(row - 1, col);
        event.preventDefault();
        break;
      case 'ArrowDown':
        this.moveFocus(row + 1, col);
        event.preventDefault();
        break;
      case 'ArrowLeft':
        if ((target as HTMLInputElement).selectionStart === 0) {
          this.moveFocus(row, col - 1);
          event.preventDefault();
        }
        break;
      case 'ArrowRight':
        if ((target as HTMLInputElement).selectionEnd === (target as HTMLInputElement).value.length) {
          this.moveFocus(row, col + 1);
          event.preventDefault();
        }
        break;
      case 'Enter':
        this.moveFocus(row + 1, col);
        event.preventDefault();
        break;
      case 'Tab':
        if (col === this.appExcelNavCols - 1) {
          if (row === this.appExcelNavRows - 1) {
            this.addRow.emit();
            // Focus will be handled by the component after row is added
          } else {
            this.moveFocus(row + 1, 0);
            event.preventDefault();
          }
        }
        break;
      case 'Escape':
        target.blur();
        break;
    }
  }

  @HostListener('paste', ['$event'])
  handlePaste(event: ClipboardEvent) {
    const clipboardData = event.clipboardData;
    if (!clipboardData) return;

    const pastedText = clipboardData.getData('text');
    if (pastedText.includes('\t') || pastedText.includes('\n')) {
      event.preventDefault();
      const rows = pastedText.split(/\r?\n/).filter(row => row.trim().length > 0);
      const data = rows.map(row => row.split('\t'));
      this.pasteData.emit(data);
    }
  }

  private moveFocus(row: number, col: number) {
    const nextElement = this.el.nativeElement.querySelector(`[data-row="${row}"][data-col="${col}"]`) as HTMLElement;
    if (nextElement) {
      nextElement.focus();
      if (nextElement instanceof HTMLInputElement) {
        nextElement.select();
      }
    }
  }
}
