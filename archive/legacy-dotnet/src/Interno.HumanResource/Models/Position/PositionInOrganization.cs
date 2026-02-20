using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Interno.HumanResource.Models
{
    public class PositionInOrganization
    {
        [KeyAttribute]
        public int Id { get; set; }
        public ICollection<JobPosition> SuperiorBoss { get; set; }
        public ICollection<JobPosition> InmediateBoss { get; set; }
        public ICollection<JobPosition> Subordinates { get; set; }

        public int NumberOfSubordinates { get; set; }
        public int NumberOfSubordinatedOccupants { get; set; }
        [NotMapped]
        public virtual ICollection<PositionMobility> Mobility { get; set; }
        
    }
}