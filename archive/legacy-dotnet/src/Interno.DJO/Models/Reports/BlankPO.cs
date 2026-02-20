using System;
using System.ComponentModel.DataAnnotations;
namespace Interno.DJO.Models
{
    public class BlankPO
    {
        [Key]
        public int Id { get; set; }
        public string FOB { get; set; }
        public string Terms { get; set; }
        public decimal AgreedUnitPrice { get; set; }
        public string BuyerName { get; set; }
        public string CurrencyCode { get; set; }
        public string ItemDescription { get; set; }
        public int Line { get; set; }
        public int PO { get; set; }
        public string TypePO { get; set; }
        public decimal QtyOutstanding { get; set; }
        public decimal AmountOutstanding { get; set; }
        public string ReleaseAuthStatus { get; set; }
        public string ReleaseCloseCode { get; set; }
        public int ReleaseNumber { get; set; }
        public string ShipToOrg { get; set; }
        public string ShipmentType { get; set;}
        public string Vendor { get; set; }
        public string Item { get; set; }
        public DateTime NeedByDate { get; set; }
        public DateTime POCreationDate { get; set; }
        public DateTime CreationDate { get; set; }
        public DateTime PromisedDate { get; set; }
        public DateTime ReleaseDate { get; set; }
        
    }
}