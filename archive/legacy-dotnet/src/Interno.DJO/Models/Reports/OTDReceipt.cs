using System;
using System.ComponentModel.DataAnnotations;
namespace Interno.DJO.Models
{
    public class OTDReceipt
    {
        [Key]
        public int Id { get; set; }
        public string OrganizationCode { get; set; }
        public string Type { get; set; }
        public string Item { get; set; }
        public string Vendor { get; set; }
        public int PO { get; set; }
        public int Line { get; set; }
        public int Release { get; set; }
        public int POshipmentNumber { get; set; }
        public DateTime ReceiptCreationDate { get; set; }
        public decimal QuantityReceived { get; set; }
        public string Buyer { get; set; }
        public decimal PrimaryQuantity { get; set; }
        public DateTime PromisedDate { get; set; }
        public string TransactionType { get; set; }
        public string TransactionType2 { get; set; }

        public virtual bool OnTime { get; set;}

    }
}