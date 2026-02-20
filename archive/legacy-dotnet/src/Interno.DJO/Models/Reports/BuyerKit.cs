using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;

namespace Interno.DJO.Models
{
    public class BuyerKit
    {
        [Key]
        public int Id { get; set; }
        public DateTime Date { get; set; }
        public string Item { get; set; }
        public string Site { get; set; }
        public string SRC { get; set; }
        public string Type { get; set; }
        public string Status { get; set; }
        public string ABC { get; set; }
        public string Buyer { get; set; }
        public string ItemDescription { get; set; }
        public DateTime FirstShortage { get; set; }
        public decimal DOS { get; set; }
        public decimal SS { get; set; }
        public string UOM { get; set; }
        public decimal LT { get; set; }
        public decimal Min { get; set; }
        public decimal Max { get; set; }
        public decimal Multi { get; set; }
        public string Supplier { get; set; }
        public decimal OH { get; set; }
        public decimal PO { get; set; }
        public decimal PLO { get; set; }
        public decimal DMD { get; set; }
    }
}