using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using System.Collections.Generic;

namespace Interno.DJO.Models.Production
{
    public class Bin
    {
        [Key]
        [StringLength(50)]
        public int Id { get; set; }
        [StringLength(50)]
        public string Item { get; set; }
        [StringLength(50)]
        public string Resource { get; set; }
        [StringLength(50)]
        public string SubResource { get; set; }
        [StringLength(50)]
        public string Location { get; set; }
        public int Qty { get; set; }
        [StringLength(50)]
        public string Logo { get; set; }
        public int Hours { get; set; }
        [StringLength(5)]
        public string UOM { get; set; }
        [StringLength(50)]
        public string PackingType { get; set; }
        [StringLength(50)]
        public string BinSize { get; set; }
        public int QtyBines { get; set; }
        [StringLength(50)]
        public string Color { get; set; }
        [StringLength(50)]
        public string SubInvetorySource { get; set; }
        [StringLength(50)]
        public string LocatorSource { get; set; }
        [NotMapped]
        public virtual ICollection<Assortment> Assortments {get; set;}
        [NotMapped]
        public string Description { get; set; }
        public bool Bloqued { get; set; }
    }
}