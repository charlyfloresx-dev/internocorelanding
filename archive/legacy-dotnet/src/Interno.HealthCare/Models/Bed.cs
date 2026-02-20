using System;
using System.ComponentModel.DataAnnotations;
using Interno.Domain.Enum;

namespace Interno.HealthCare.Models
{
    public class Bed
    {
        [KeyAttribute]
        public int Id { get; set; }
        [RequiredAttribute]
        [MaxLengthAttribute(45)]
        public string Code { get; set; }
        [RequiredAttribute]
        public BedType BedType { get; set; }
        [RequiredAttribute]
        public Interno.Domain.Enum.StatusType Status { get; set; }
        [RequiredAttribute]
        [DataType(DataType.Date)]
        public DateTime AvailabilityFromDate { get; set; }
        [DataType(DataType.Date)]
        public DateTime ExpiredDate { get; set; }   
    }
}