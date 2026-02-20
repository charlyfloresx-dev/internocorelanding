using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;

namespace Interno.DJO.Models
{
    public class STBLOnHandBuildReport
    {
        
        [Key]
        public int Id { get; set; }
        public string PartName { get; set; }
        public string Description { get; set; }
        public string Site { get; set; }
        public string Type { get; set; }
        public string SourceType { get; set; }
        public string Source { get; set; }
        public string Buyer { get; set; }
        public string Cell { get; set; }
        public string OrderType { get; set; }
        public string Status { get; set; }
        public string DemandPlanSegment { get; set; }
        public string OrderLine { get; set; }
        public string CorporateBrand { get; set; }
        public DateTime RequestDate { get; set; }
        public int ShortCompCount { get; set; }
        public char Hold { get; set; }
        public decimal Quantity { get; set; }
        public decimal UnitSellingPrice { get; set; }
        public decimal ExtValue { get; set; }
        public decimal FGOnHandQty { get; set; }
        public int OnHandBuildQty { get; set; }
        public int QtyOnWorngOrg { get; set; }
        public decimal TotalBuildQuantity { get; set; }
        public int STBLQtyInpanct { get; set; }
        public decimal NetOH { get; set; }
        public string RoutCauses { get; set; }
        public string Notes { get; set; }
        public string Supplier { get; set; }
        public string MfgPfg { get { return (this.SourceType != "Make") ? "PFG" : "MFG"; } }
        public string Component { get; set; }
        public DateTime ComponentDueDate { get; set; }
        public virtual ICollection<BOM> BOM { get; set; }
        public virtual ICollection<SupplyDemand> SupplyDemand { get; set; }
        public virtual BOM ComponentAffect { get; set; }
        public virtual ISTBLComp NotesData { get; set; }
        public string Category { get; set; }
        public string Module { get; set; }
    }

    public class ISTBLComp
    {
        public string Type { get; set; }
        public string Comp { get; set; }
        public DateTime DueDate { get; set; }
    }
}