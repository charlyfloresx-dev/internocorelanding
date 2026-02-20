using System.ComponentModel.DataAnnotations;
namespace Interno.HumanResource.Models.Catalog
{
    public class Competence
    {
        [KeyAttribute]
        public int Id { get; set; }
        [RequiredAttribute]
        public CompetencesType Type { get; set; }
        [RequiredAttribute]
        [MaxLength(250)]
        public string Characteristic { get; set; }
        
    }
    public enum CompetencesType
    {
        Generic = 1,
        Management = 2,
        Behavioral = 3
    }
}