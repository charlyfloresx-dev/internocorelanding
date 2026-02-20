using System.ComponentModel.DataAnnotations;
using Interno.Domain.Catalog;

namespace Interno.HumanResource.Models
{
    public class PositionLanguage
    {
        [KeyAttribute]
        public int Id { get; set; }
        [RequiredAttribute]
        [MaxLength(45)]
        public string Language { get; set; }
        [RequiredAttribute]
        public Level Level { get; set; }
        [RequiredAttribute]
        public Required Required { get; set; }
    }
}