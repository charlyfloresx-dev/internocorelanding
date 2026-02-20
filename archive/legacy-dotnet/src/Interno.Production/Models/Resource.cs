
using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations.Schema;

namespace Interno.Production.Models
{
    public class Resource : Interno.Inventory.Models.Warehouse
    {
        [NotMapped]
        public int BreakGroupId { get; set; }
        [NotMapped]
        public virtual Interno.HumanResource.Models.Catalog.BreaksGroup BreakGroup { get; set; }
        /*
            public int Id { get; set; }
            public string Code { get; set; }
            public string Name { get; set; }
            public string Description { get; set; }
            public virtual WarehouseType Type { get; set; }
                public int Id { get; set; }
                public string Name { get; set; }
                public string Decription { get; set; }
            public float Capacity { get; set; }
            public virtual Interno.Domain.Catalog.UM Unit { get; set; }
            public virtual WarehouseGroup Group { get; set; }
            public DateTime Updated { get; set; } = DateTime.UtcNow;
            public DateTime DeleteDate { get; set;}
            public bool Delete { get; set; }
            public bool Active { get; set; }
        */
        [NotMapped]
        public ProductionArea Area { get; set; }
        /* 
            public int Id { get; set; }
            public string Name { get; set; }
            public string Description { get; set; }
            public Facility Facility { get; set; }
                public int Id { get; set; }
                public string Code { get; set; }
                public string Name { get; set; }
                public Interno.Domain.Catalog.Location Location { get; set; }
                public virtual ICollection<Interno.Inventory.Models.Warehouse> Warehouses { get; set; }
        */
        //[NotMapped]
        //public virtual ICollection<Interno.Domain.Catalog.Miscellaneous> Miscellaneous { get; set; } = new List<Interno.Domain.Catalog.Miscellaneous>();
    }
}