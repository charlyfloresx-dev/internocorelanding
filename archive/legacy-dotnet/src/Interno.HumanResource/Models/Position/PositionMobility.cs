using System.ComponentModel.DataAnnotations;

namespace Interno.HumanResource.Models
{
    public class PositionMobility
    {
        [KeyAttribute]
        public int Id { get; set; }
        [RequiredAttribute]
        public JobPosition JobPosition { get; set; }
        [RequiredAttribute]
        public MobilityType Type { get; set; }
    }
}