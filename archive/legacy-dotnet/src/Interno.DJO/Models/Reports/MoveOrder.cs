using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
namespace Interno.DJO.Models
{
    public class MoveOrder
    {
        [Key]
        public int Id { get; set; }
        public long Number { get; set; }
        public string Description { get; set; }
        public DateTime CreatedDateTime { get; set; }
        public string Type { get; set; }
        public int Line { get; set; }
        public string TransactionType { get; set; }
        public string Item { get; set; }
        public string Rev { get; set; }
        public string SourceSubinv { get; set; }
        public string SourceLocator { get; set; }
        public string DestinationSubinv { get; set; }
        public string DestinationLocator { get; set; }
        public string DestinationAcoount { get; set; }
        public string LotNumber { get; set; }
        public DateTime ExpirationDate { get; set; }
        public string SerialFrom { get; set; }
        public string SerialTo { get; set; }
        public string UnitNumber { get; set; }
        public string UOM { get; set; }
        public decimal TransactionQty { get; set; }
        public decimal RequestedQty { get; set; }
        public DateTime TransactionDate { get; set; }
        public bool OnTimeMetric { get; set; }
        public decimal RequiredQty { get; set; }
        public decimal DeliveredQty { get; set; }
        public decimal AllocatedQty { get; set; }
        public decimal RemainingQty { get; set; }
        public string SecondaryUOM { get; set; }
        public decimal SecondaryQty { get; set; }
        public decimal SecondaryRequestedQty { get; set; }
        public decimal SecondatyRequiredQty { get; set; }
        public decimal SecondaryDeliveredQty { get; set; }
        public decimal SecondaryAllocatedQty { get; set; }
        public string Grade { get; set; }
        public DateTime DateRequired { get; set; }
        public string Reason { get; set; }
        public string Reference { get; set; }
        public string Route { get; set; }
        public string Cell { get; set; }
        public string Priority { get; set; }
        public string LineStatus { get; set; }
        public DateTime StatusDate{ get; set; }
        public string CreatedBy { get; set; }
        public double ShortTime { get{ return (this.DateRequired - this.CreatedDateTime).TotalHours ;} }

        //Internal Control
        
        public Interno.Domain.Enum.PriorirtyLevel PriorityLevel { get; set; }
        public DateTime AssortmenStart { get; set; }
        public int AssortmentUser { get; set; }
        public Interno.Domain.Enum.StatusType Status { get; set; }

        [TimestampAttribute]
        [DatabaseGenerated (DatabaseGeneratedOption.Computed)]
        public DateTime Updated { get; set; } = DateTime.UtcNow;

    }    
}