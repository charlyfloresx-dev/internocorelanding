using System;
using System.ComponentModel.DataAnnotations;
namespace Interno.DJO.Models
{
    public class BalanceOnHand
    {
        [Key]
        public int Id { get; set; }
        public string Customer { get; set; }
        public int ReceiveingId { get; set; }
        public int ControlNumber { get; set; }
        public string PartNumber { get; set; }
        public string Description { get; set; }
        public string Status { get; set; }
        public string Type { get; set; }
        public DateTime ReceivedDate { get; set; }
        public int Qty { get; set; }
        public string Unit { get; set; }
        public int Bal { get; set; }
        public int DaysIn { get; set; }
        public string Location { get; set; }
        public int Weight { get; set; }
        public string Shipper { get; set; }
        public string PO { get; set; }
        public string Carrier { get; set; }
        public string FB { get; set; }
        public int Inbond { get; set; }
        public DateTime InbondIssueDate { get; set; }
        public string Comments { get; set; }
        public string Reference { get; set; }
    }
}