using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
namespace Interno.DJO.Models
{
    public class BOM
    {
        [Key]
        public int Id { get; set; }
        
        public string Item { get; set; }
        public string Description { get; set; }
        public string Type { get; set; }
        public string TypeDescription { get; set; }
        public string Module { get; set; }
        public string Status { get; set; }
        public int Level { get; set; }
        
        public string Parent { get; set; }
        
        public string Component { get; set; }
        public string ComponentDescription { get; set; }
        public decimal ComponenQuantityPer { get; set; }
        public string UOM { get; set; }
        public string ComponentType { get; set; }
        public string ComponentModule { get; set; }
        public string ComponentSupplierType { get; set; }

        public virtual ICollection<SupplyDemand> SupplyDemand {get; set;}
        public virtual OpenSummaryReport OpenSummaryReport {get; set;}
        public virtual DateTime DueDate { get; set;}
        public virtual double Backorder {get; set;}
    }
}