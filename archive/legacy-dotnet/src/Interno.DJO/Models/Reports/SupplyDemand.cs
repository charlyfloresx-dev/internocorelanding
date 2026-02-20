using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using Interno.DJO.Helpers;

namespace Interno.DJO.Models
{
    public class SupplyDemand
    {
        [Key]
        public int Id { get; set; }
        public string Item { get; set; }
        public string Description { get; set; }
        public string Type { get; set; }
        public string Site { get; set; }
        public string Cell { get; set; }
        public string Buyer { get; set; }
        public string Supplier { get; set; }
        public string ABC { get; set; }
        public decimal LeadTime { get; set; }
        public DateTime LTDate { get; set; }
        public DateTime ShortageDate { get; set; }
        public decimal StdUnitCost { get; set; }
        public decimal SafetyStockQty { get; set; }
        public decimal OnHand { get; set; }
        public decimal OpenPOs { get; set; }
        public OpenSummaryReport OpenSummaryReport { get; set; }
        public virtual DateTime DueDate { get; set; }
        public virtual int Week {get; set;}
        public virtual ICollection<ProjectedDate> ProjectedDates { get; set; }
        public virtual ICollection<BOM> BOM {get; set;}
    }

    public class ProjectedDate
    {
        [Key]
        public int Id { get; set; }
        public DateTime Date { get; set; }
        public string Type { get; set; }
        public decimal Qty { get; set; }
        public SupplyDemand SupplyDemand { get; set; }
        public virtual int Week { get{ return (Date != DateTime.MinValue)? Date.WeekOfYear() : 0;}}
    }
}