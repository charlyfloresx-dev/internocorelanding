using System;
using System.ComponentModel.DataAnnotations;

namespace Interno.DJO.Models
{
    public class Quotation
    {
        [Key]
        public int Quote { get; set; }
        [Key]
        public int Line { get; set; }
        public string Item { get; set; }
        public string Description { get; set; }
        public string Buyer { get; set; }
        public DateTime Creation { get; set; }
        public string SupplierItem { get; set; }
        public string Vendor { get; set; }
        public string VendorSite { get; set; }
        public char Status { get; set; }
        public DateTime LastUpdate { get; set; }
        public string ShipTo { get; set; }
        public string EefTo { get; set; }
        public string EefFrom { get; set; }
        public string BillTo { get; set; }
        public string Term { get; set; }
        public string Type { get; set; }
        public string UOM { get; set; }
        public decimal UnitPrice { get; set; }
    }
}