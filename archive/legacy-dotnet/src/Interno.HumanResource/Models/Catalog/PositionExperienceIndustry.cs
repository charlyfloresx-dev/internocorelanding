using System.ComponentModel.DataAnnotations;

namespace Interno.HumanResource.Models.Catalog
{
    public class PositionExperienceIndustry
    {
        [KeyAttribute]
        public int Id { get; set; }
        [RequiredAttribute]
        [MaxLength(45)]
        public string Industry { get; set; }
        [RequiredAttribute]
        public int Years { get; set; }
    }
}