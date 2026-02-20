using System;
using System.ComponentModel.DataAnnotations;
namespace Interno.Inventory.Models
{
    public class BOM
    {
        [KeyAttribute]
        public int Id { get; set; }
        [RequiredAttribute]
        public Item Item { get; set; }
        [RequiredAttribute]
        public Item Component { get; set; }
        [RequiredAttribute]
        public float Quantity { get; set; }
        [RequiredAttribute]
        public Interno.Domain.Catalog.UM Unit { get; set; }
        [Required]
        public int Level { get; set; }



        [TimestampAttribute]
        public DateTime CreateDate { get; set;}
        [DataType(DataType.DateTime)]
        public DateTime UpdateDate { get; set;}
        [DataType(DataType.DateTime)]
        public DateTime DeleteDate { get; set;}
        [MaxLength(45)]
        public string LastUser { get; set; }
    }
}