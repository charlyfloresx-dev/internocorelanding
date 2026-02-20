using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;

using Interno.Inventory.Models;

using Interno.Domain.Catalog;

namespace Interno.HealthCare.Models
{
    public class MedicalRecord
    {
        [KeyAttribute]
        public int Id { get; set; }
        [RequiredAttribute]
        public MedicalRecordType Type { get; set; }
        [RequiredAttribute]
        [DataType(DataType.Date)]
        public DateTime Date { get; set; }
        [RequiredAttribute]
        public HospitalUser Patient { get; set; }
        public HospitalUser Specialist { get; set; }
        public Room Room { get; set; }


        [RequiredAttribute]
        public string Purpose { get; set; }
        public string Description { get; set; }

        public virtual ICollection<Interno.Inventory.Models.Document> Prescription { get; set; } = new List<Document>();

        public virtual ICollection<Interno.Domain.Catalog.Miscellaneous> Undergoes { get; set; } = new List<Miscellaneous>(); //Padecimientos

        public virtual ICollection<HealthCare> Care { get; set; } = new List<HealthCare>(); // Terapias Cuidados
        
        public virtual ICollection<Interno.Domain.Catalog.Miscellaneous> Miscellaneous { get; set; } = new List<Miscellaneous>();
        [RequiredAttribute]
        public Interno.Domain.Enum.StatusType Status { get; set; }

    }
}