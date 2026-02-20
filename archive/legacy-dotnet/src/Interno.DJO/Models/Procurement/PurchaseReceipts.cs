using System;
using System.ComponentModel.DataAnnotations;
namespace Interno.DJO.Models
{
    public class PurchaseReceipts
    {
        [Key]
        public int Id { get; set; }
        public int PO { get; set; }
        public int Line { get; set; }
        public decimal POQty { get; set;}
        public DateTime ReceivedDate { get; set; }
        public decimal ReceivedQty { get; set; }
        public string Product { get; set; }
        public string SupplierName { get; set; }
        public string VendorType { get; set; }
        public string ProductName { get; set; }
        public string ProductType { get; set; }
        public string Site { get; set; }
        public DateTime POCreationDate { get; set; }
        public DateTime POReleaseDate { get; set; }
        public DateTime PromisedDate { get; set; }
        public string Buyer { get; set; }
        public int FiscalYear { get; set; }
        public string FiscalQuarter { get; set; }
        public string FiscalPeriod { get; set; }
        public string FiscalWeek { get; set; }
        public decimal ReceiptAmount { get; set; }
        public decimal ReceivedPrice { get; set; }
        public virtual string Category { get; set; }
        public virtual decimal StdCost { get; set; }
        public virtual decimal StdCostExt { get; set; }
        public virtual decimal PPV { get; set; }
        public virtual decimal Spend { get; set; }
        public virtual decimal Excess { get{ return (this.POQty != 0 && this.ReceivedQty > this.POQty)? this.ReceivedQty - this.POQty:0; }}

        // public virtual decimal StdCostExt = (StdCost != 0)? Decimal.Round(StdCost*this.ReceivedQty,6) : this.ReceivedPrice ;} }
        // public virtual decimal PPV = Decimal.Round((StdCostExt != 0)? this.ReceiptAmount - StdCostExt : 0,6);  } }
        // public virtual decimal Spend = Decimal.Round( ReceiptAmount - PPV,6);} }
    }
}