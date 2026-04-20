import { Directive, ElementRef, HostListener, Input, Output, EventEmitter, inject } from '@angular/core';

@Directive({
  selector: '[icExcelNav]',
  standalone: true
})
export class ExcelNavigationDirective {
  @Input('icExcelNav') rows: any[] = [];
  @Input() skipCols: number[] = [];
  
  @Output() lastCellTab = new EventEmitter<void>();
  @Output() smartPaste = new EventEmitter<string[][]>();

  private el = inject(ElementRef);

  @HostListener('keydown', ['$event'])
  onKeyDown(event: KeyboardEvent) {
    const target = event.target as HTMLElement;
    const cell = target.closest('[data-col]') as HTMLElement;
    const rowEl = target.closest('[data-row]') as HTMLElement;
    
    if (!cell || !rowEl) return;

    const row = parseInt(rowEl.getAttribute('data-row') || '0');
    const col = parseInt(cell.getAttribute('data-col') || '0');

    // Handle Enter like Excel (Move Down)
    if (event.key === 'Enter') {
      const isLastRow = row === this.rows.length - 1;
      const isLastCol = col === this.getNextCol(col) || this.getNextCol(col) === -1;
      
      if (isLastRow && col >= 1) { // If we are at the end, add new row
        this.lastCellTab.emit();
        return;
      }
      
      this.focusCell(row + 1, col);
      event.preventDefault();
      return;
    }

    switch (event.key) {
      case 'ArrowUp':
        // Allow numeric incrementing if it's a number input (without Ctrl)
        if (target instanceof HTMLInputElement && target.type === 'number' && !event.ctrlKey) {
          return; 
        }
        this.focusCell(row - 1, col);
        event.preventDefault();
        break;
      case 'ArrowDown':
        // Allow numeric decrementing if it's a number input (without Ctrl)
        if (target instanceof HTMLInputElement && target.type === 'number' && !event.ctrlKey) {
          return; 
        }
        this.focusCell(row + 1, col);
        event.preventDefault();
        break;
      case 'ArrowLeft':
        if (target instanceof HTMLInputElement && (target.selectionStart === 0 || target.type === 'number' || event.ctrlKey)) {
          this.focusCell(row, this.getPrevCol(col));
          event.preventDefault();
        }
        break;
      case 'ArrowRight':
        if (target instanceof HTMLInputElement && (target.selectionEnd === target.value.length || target.type === 'number' || event.ctrlKey)) {
          this.focusCell(row, this.getNextCol(col));
          event.preventDefault();
        }
        break;
      case 'Tab':
        if (!event.shiftKey) {
          const nextCol = this.getNextCol(col);
          if (nextCol === -1) { // End of row
            if (row === this.rows.length - 1) {
              this.lastCellTab.emit();
              // event.preventDefault();
            } else {
              // Move to next row, first column
              this.focusCell(row + 1, 0);
              event.preventDefault();
            }
          }
        } else {
            // Shift + Tab
            const prevCol = this.getPrevCol(col);
            if (prevCol === -1 && row > 0) {
                this.focusCell(row - 1, this.getMaxCol());
                event.preventDefault();
            }
        }
        break;
    }
  }

  private getMaxCol(): number {
      let max = 0;
      while (this.el.nativeElement.querySelector(`[data-col="${max + 1}"]`)) max++;
      return max;
  }

  @HostListener('paste', ['$event'])
  onPaste(event: ClipboardEvent) {
    const data = event.clipboardData?.getData('text');
    if (!data) return;

    if (data.includes('\n') || data.includes('\t')) {
      event.preventDefault();
      const rows = data.split(/\r?\n/)
        .map(r => r.split('\t').map(c => c.trim()))
        .filter(r => r.length > 0 && r[0] !== '');
      
      this.smartPaste.emit(rows);
    }
  }

  private getNextCol(col: number): number {
    let next = col + 1;
    while (this.skipCols.includes(next)) next++;
    // Check if next exists in template
    const exists = this.el.nativeElement.querySelector(`[data-col="${next}"]`);
    return exists ? next : -1;
  }

  private getPrevCol(col: number): number {
    let prev = col - 1;
    while (this.skipCols.includes(prev)) prev--;
    return prev;
  }

  private focusCell(row: number, col: number) {
    if (col === -1) return;
    const next = this.el.nativeElement.querySelector(
      `[data-row="${row}"] [data-col="${col}"] input, [data-row="${row}"] [data-col="${col}"] select`
    ) as HTMLElement;
    
    if (next) {
      next.focus();
      if (next instanceof HTMLInputElement) {
        next.select();
      }
    }
  }
}
