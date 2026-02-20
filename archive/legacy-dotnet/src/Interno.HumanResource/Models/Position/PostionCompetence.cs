using System.ComponentModel.DataAnnotations;
using Interno.HumanResource.Models.Catalog;
using Interno.Domain.Catalog;
namespace Interno.HumanResource.Models
{
    public class PositionCompetences : Interno.HumanResource.Models.Catalog.Competence
    {   
        [RequiredAttribute]
        public Level Level { get; set; }
        [RequiredAttribute]
        public Required Required { get; set; }
    }
}