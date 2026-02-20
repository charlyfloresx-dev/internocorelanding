using System;
using System.ComponentModel.DataAnnotations;

namespace Interno.Inventory.Models
{
    public class Movements
    {
        [KeyAttribute]
        public int Id { get; set; }

        public Item Product { get; set; }
        
        public Interno.Domain.Catalog.UM Unit { get; set; }

        public float Quantity { get; set; }

        public float PurchasePrice { get; set; }
        public float SellPrice { get; set; }

        public float Total { get; set; }

        public bool AffectedStock { get; set; }

        [TimestampAttribute]
        public DateTime CreateDate { get; set;}
        [DataType(DataType.DateTime)]
        public DateTime UpdateDate { get; set;}
        [DataType(DataType.DateTime)]
        public DateTime DeleteDate { get; set;}
        [MaxLength (45)]
        public string LastUser { get; set; }
    }
    
}