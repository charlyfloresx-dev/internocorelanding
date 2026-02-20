using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using Interno.Domain.Catalog;

namespace Interno.HealthCare.Models
{
    public class HospitalUser
    {
        [Key]
        public int Id { get; set; }
        [Required]
        public Person Person { get; set; }
        [Required]
        public SpecialistType Role { get; set; }
        //If Employee
        public Interno.HumanResource.Models.Employee Employee { get; set; }

        public ICollection<Specialty> Specialties { get; set; } = new List<Specialty>();

        public ICollection<Care> CareSpecialist { get; set; } = new List<Care>();

        public ICollection<Interno.Domain.Catalog.Contact> Contact { get; set; } = new List<Contact>();
    }
}