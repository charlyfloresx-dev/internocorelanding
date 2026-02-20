using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using System.Collections.Generic;
using Interno.Domain.Catalog;

namespace Interno.Inventory.Models
{
    public class Item
    {
        [Key, Required]
        public Guid Guid { get; set; }
        [Key, Required, MaxLength(45)]
        public string Code { get; set; }
        [Required]
        [MaxLength(45)]
        public string Name { get; set; }
        [Required]
        [MaxLength(250)]
        public string Description { get; set; }
        public virtual ProductCategory Category { get; set; } //Product/ Equipment
        [MaxLength(45)]
        public string Alias { get; set; }
        public bool Active { get; set; }
        [MaxLength(5)]
        public string Revision { get; set; }
        public virtual Interno.Domain.Enum.StatusType Status { get; set; }

        //public Equipment Equipment { get; set; }

        public float Weight { get; set; }
        public float Length { get; set; }
        public float Width { get; set; }
        public float Height { get; set; }
        public Interno.Domain.Catalog.UM Unit { get; set; }

        public float MinOrderQty { get; set; }//MinimumOrderQty
        public float MaxOrderQty { get; set; }//MaxOrderQty
        public float SafetyStock { get; set; }
        public float ReorderPoint { get; set; }
        public float OrderMultiple { get; set; }

        //Data
        //public FileData Image { get; set; }
        //public FileData Drawing { get; set; }
        [NotMapped]
        public ICollection<BOM> BOM { get; set; } = new List<BOM>();

        public Item()
        {
            Active = true;
            Guid = Guid.NewGuid();
        }
        [TimestampAttribute]
        public DateTime CreateDate { get; set; }
        [DataType(DataType.DateTime)]
        public DateTime UpdateDate { get; set; }
        [DataType(DataType.DateTime)]
        public DateTime DeleteDate { get; set; }
        [MaxLength(45)]
        public string LastUser { get; set; }
    }
}