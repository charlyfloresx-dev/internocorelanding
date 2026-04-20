import { Directive, ElementRef, HostListener, Output, EventEmitter, inject } from '@angular/core';

@Directive({
  selector: '[icExcelNav]',
  standalone: true
})
export class ExcelNavigationDirective {
  @Output() smartPaste = new EventEmitter<string[][]>();
  @Output() lastCellTab = new EventEmitter<void>();

  private el = inject(ElementRef);

  @HostListener('keydown', ['$event'])
  onKeyDown(event: KeyboardEvent) {
    const target = event.target as HTMLElement;
    const isInput = target.tagName === 'INPUT' || target.tagName === 'SELECT' || target.contentEditable === 'true';
    
    if (!isInput) return;

    const row = parseInt(target.getAttribute('data-row') || '-1', 10);
    const col = parseInt(target.getAttribute('data-col') || '-1', 10);

    if (row === -1 || col === -1) return;

    switch (event.key) {
      case 'ArrowUp':
        this.navigate(row - 1, col, event);
        break;
      case 'ArrowDown':
        this.navigate(row + 1, col, event);
        break;
      case 'ArrowLeft':
        // Only navigate if at the start of input or not an input text
        if (this.isAtStart(target)) {
          this.navigate(row, col - 1, event);
        }
        break;
      case 'ArrowRight':
        // Only navigate if at the end of input or not an input text
        if (this.isAtEnd(target)) {
          this.navigate(row, col + 1, event);
        }
        break;
      case 'Enter':
        // Enter moves down by default in many industrial systems
        this.navigate(row + 1, col, event);
        break;
      case 'Tab':
        // Check if last cell of the current row to trigger addRow logic
        const maxCol = this.getMaxCol(row);
        if (col === maxCol && !event.shiftKey) {
          // Check if no row below exists
          const nextRow = this.findCell(row + 1, 0);
          if (!nextRow) {
            this.lastCellTab.emit();
            // Don't prevent default, let Tab create the row and focus the new one if possible
          }
        }
        break;
    }
  }

  @HostListener('paste', ['$event'])
  onPaste(event: ClipboardEvent) {
    const clipboardData = event.clipboardData;
    if (!clipboardData) return;

    const pastedText = clipboardData.getData('text');
    if (pastedText.includes('\t') || pastedText.includes('\n')) {
      event.preventDefault();
      const rows = pastedText.split(/\r?\n/).filter(r => r.trim().length > 0).map(r => r.split('\t'));
      if (rows.length > 0) {
        this.smartPaste.emit(rows);
      }
    }
  }

  private navigate(row: number, col: number, event: Event) {
    const cell = this.findCell(row, col);
    if (cell) {
      event.preventDefault();
      cell.focus();
      if (cell instanceof HTMLInputElement) {
        cell.select();
      }
    }
  }

  private findCell(row: number, col: number): HTMLElement | null {
    return this.el.nativeElement.querySelector(`[data-row="${row}"][data-col="${col}"]`);
  }

  private getMaxCol(row: number): number {
    const cells = this.el.nativeElement.querySelectorAll(`[data-row="${row}"][data-col]`);
    let max = -1;
    cells.forEach((c: HTMLElement) => {
      const col = parseInt(c.getAttribute('data-col') || '-1', 10);
      if (col > max) max = col;
    });
    return max;
  }

  private isAtStart(target: HTMLElement): boolean {
    if (target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement) {
      return target.selectionStart === 0 && target.selectionEnd === 0;
    }
    return true;
  }

  private isAtEnd(target: HTMLElement): boolean {
    if (target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement) {
      return target.selectionStart === target.value.length;
    }
    return true;
  }
}
