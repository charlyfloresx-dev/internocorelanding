using System;
using System.ComponentModel.DataAnnotations;
namespace Interno.DJO.Models
{
    public class PlannedPO
    {
        [Key]
        public int Id { get; set; }
        public string Item { get; set; }
        public string Description { get; set; }
        public string Site { get; set; }
        public string Type { get; set; }
        public string Status { get; set; }
        public string Buyer { get; set; }
        public string Supplier { get; set; }
        public decimal StdCost { get; set; }
        public string SupplyType { get; set; }
        public int Line { get; set; }
        public decimal EffQty { get; set; }
        public int LeadTime { get; set; }
        public int DaysToAcc { get; set; }
        public string Action { get; set; }
        public DateTime StartDate { get; set; }
        public DateTime DueDate { get; set; }
        public virtual string Category { get; set;}
        public virtual decimal StdCostExt { get; set; }
        public virtual decimal PPV { get; set; }
        public virtual decimal Spend { get; set; }
    }
}