using System;
using System.ComponentModel.DataAnnotations;
namespace Interno.DJO.Models
{
    public class OpenSummaryReport
    {
        [Key]
        public int Id { get; set; }
        public string Site { get; set; }
        public string Part { get; set; }
        public string Description { get; set; }
        public string Buyer { get; set; }
        public string Organization { get; set; }
        public string Order { get; set; }

        public string Line { get; set; }
        public string OrderType { get; set; }
        public string Supplier { get; set; }
        public string SupplierDescription { get; set; }
        public string UOM { get; set; }
        public string Status { get; set; }

        public decimal OrgQuantity { get; set; }
        public decimal OpenQuantity { get; set; }
        public string ShipTo { get; set; }
        public DateTime DueDate { get; set; }
        public DateTime OriginalDueDate { get; set; }
        public decimal UnitPrice { get; set; }
        public decimal Amount { get; set; }
        public DateTime? FirstShortageDate { get; set; }
        public DateTime? RecomendedDate { get; set; }

    }
}