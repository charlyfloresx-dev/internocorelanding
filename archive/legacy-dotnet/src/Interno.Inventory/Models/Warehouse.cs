using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Interno.Inventory.Models
{
    public class Warehouse
    {
        
        [Key,Required]
        [MaxLength (13)]
        public string Code { get; set; }

        [Required]
        [MaxLength (100)]
        public string Name { get; set; }

        [MaxLength (250)]
        public string Description { get; set; }
        
        [Required]
        public int TypeId { get; set; }
        public virtual WarehouseType Type { get; set; }
        public float Capacity { get; set; }
        [MaxLength (4)]
        public string UnitCode { get; set; }
        public virtual Interno.Domain.Catalog.UM Unit { get; set; }
        public virtual WarehouseGroup Group { get; set; }

        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public DateTime Created { get; set; } = DateTime.UtcNow;

        [TimestampAttribute]
        [DatabaseGenerated(DatabaseGeneratedOption.Computed)]
        public DateTime Updated { get; set; } = DateTime.UtcNow;

        [DataType(DataType.DateTime)]
        public DateTime? DeleteDate { get; set;}
        public bool Delete { get; set; }
        public bool Active { get; set; }

        public Warehouse(){
            this.Active = true;
            this.DeleteDate = DateTime.MinValue;
            this.Delete = false;
        }
    }

    public class WarehouseType
    {
        [Key]
        public int Id { get; set; }

        [Required]
        [MaxLength (25)]
        public string Name { get; set; }

        [MaxLength (250)]
        public string Decription { get; set; }
        [NotMapped]
        public virtual ICollection<Warehouse> Warehouses { get; set; }
    }

    public class WarehouseGroup 
    { 
        [Key]
        public int Id { get; set; }

        [Required]
        [MaxLength (25)]
        public string Name { get; set; }

        [MaxLength (250)]
        public string Description { get; set; }
        public virtual ICollection<Warehouse> Warehouses { get; set; }
    }
}