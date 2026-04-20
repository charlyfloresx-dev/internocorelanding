import { Injectable, inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

@Injectable({
    providedIn: 'root'
})
export class PrintService {
    private platformId = inject(PLATFORM_ID);
    private isBrowser = isPlatformBrowser(this.platformId);

    /**
     * Generates a thermal print-ready window with the provided HTML content.
     * Optimized for 80mm thermal receipt printers.
     */
    printThermalReceipt(contentHtml: string, documentTitle: string = 'InternoCore Receipt'): boolean {
        if (!this.isBrowser) return false;

        // Create a hidden iframe for printing to avoid popup blockers and UI disruption
        const iframe = document.createElement('iframe');
        iframe.style.position = 'fixed';
        iframe.style.right = '0';
        iframe.style.bottom = '0';
        iframe.style.width = '0';
        iframe.style.height = '0';
        iframe.style.border = '0';

        document.body.appendChild(iframe);

        const doc = iframe.contentWindow?.document;
        if (!doc) {
            document.body.removeChild(iframe);
            return false;
        }

        doc.open();
        doc.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>${documentTitle}</title>
          <style>
            @page {
              margin: 0;
              size: 80mm auto;
            }
            body {
              font-family: 'JetBrains Mono', 'Courier New', monospace;
              width: 72mm; /* Leave a small margin for 80mm paper */
              margin: 0 auto;
              padding: 4mm;
              font-size: 12px;
              color: #000;
              background-color: #fff;
              line-height: 1.2;
            }
            /* Reset all margins and paddings for thermal precision */
            * { box-sizing: border-box; }
            h1, h2, h3, h4, h5, h6, p { margin: 0; padding: 0; }
            
            .text-center { text-align: center; }
            .text-right { text-align: right; }
            .font-bold { font-weight: bold; }
            .text-xs { font-size: 10px; }
            .text-sm { font-size: 12px; }
            .text-lg { font-size: 16px; }
            .mb-2 { margin-bottom: 8px; }
            .mb-4 { margin-bottom: 16px; }
            .mt-4 { margin-top: 16px; }
            .pt-2 { padding-top: 8px; }
            .pb-2 { padding-bottom: 8px; }
            
            .border-t { border-top: 1px dashed #000; }
            .border-b { border-bottom: 1px dashed #000; }
            
            .flex-between { display: flex; justify-content: space-between; }
            
            /* Table specifically for receipt lines */
            table { width: 100%; border-collapse: collapse; }
            th { text-align: left; border-bottom: 1px dashed #000; padding-bottom: 4px; }
            td { padding: 2px 0; vertical-align: top; }
            .td-qty { width: 15%; text-align: left; }
            .td-desc { width: 55%; text-align: left; word-break: break-all; }
            .td-price { width: 30%; text-align: right; }
          </style>
        </head>
        <body>
          ${contentHtml}
        </body>
      </html>
    `);
        doc.close();

        // Give iframe time to render content (especially images/barcodes)
        setTimeout(() => {
            try {
                iframe.contentWindow?.focus();
                iframe.contentWindow?.print();
            } catch (e) {
                console.error('Print service failed:', e);
            } finally {
                // Cleanup after printing is done or canceled
                setTimeout(() => {
                    if (document.body.contains(iframe)) {
                        document.body.removeChild(iframe);
                    }
                }, 1000);
            }
        }, 500);

        return true;
    }
}
