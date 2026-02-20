using System;
using System.ComponentModel.DataAnnotations;

namespace Interno.DJO.Models
{
    public class Taxonomy
    {
        [Key]
        public string   ProductNumber { get; set; }
        public string ProductName { get; set; }
        public string PurchaseClass { get; set; }
        public string PurchaseCategory { get; set; }
    }
}