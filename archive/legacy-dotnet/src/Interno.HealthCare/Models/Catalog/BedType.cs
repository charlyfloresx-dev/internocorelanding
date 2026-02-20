using System.ComponentModel.DataAnnotations;
namespace Interno.HealthCare.Models
{
    public class BedType
    {
        [KeyAttribute]
        public int Id { get; set; }
        [RequiredAttribute]
        [MaxLengthAttribute(45)]
        public string Type { get; set; }
        [MaxLengthAttribute(250)]
        public string Description { get; set; }
        [RequiredAttribute]
        public bool Managed { get; set; }
    }
}