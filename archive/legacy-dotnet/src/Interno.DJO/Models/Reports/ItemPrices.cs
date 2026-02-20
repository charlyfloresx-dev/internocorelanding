using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;

namespace Interno.DJO.Models
{
    public class ItemPrice
    {
        [Key]
        public string Item { get; set; }
        public string Description { get; set; }
        public string UOM { get; set; }
        [Key]
        public string Site { get; set; }
        public string Status { get; set; }
        public string Type { get; set; }
        public string CorporateBrand { get; set; }
        public char ABC { get; set; }
        public double StdCost { get; set; }
        public string Buyer { get; set; }
        public string Supplier { get; set; }
        public decimal MOQ { get; set; }
        public decimal MPQ { get; set; }
        public decimal LeadTime { get; set; }
        public int PriorityCode { get; set; }
        public decimal SafetyStock { get; set; }
    }
}