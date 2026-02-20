using System.ComponentModel.DataAnnotations;
using Interno.Domain.Catalog;

namespace Interno.HumanResource.Models
{
     public class PositionEducation
    {
        [KeyAttribute]
        public int Id { get; set; }
        [RequiredAttribute]
        [MaxLength(250)]
        public string Characteristic { get; set; }
        [RequiredAttribute]
        public Required Required { get; set; }
    }
}