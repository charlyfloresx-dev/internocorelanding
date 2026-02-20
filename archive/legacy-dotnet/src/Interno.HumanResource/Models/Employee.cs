using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

using Interno.Domain.Catalog;
using Interno.HumanResource.Models.Catalog;

namespace Interno.HumanResource.Models
{
    public class Employee
    {
        
        public Guid Id { get; set; }
        [Key]
        public int Number { get; set; }
        [Required]
        public Person Person { get; set; } 
        [Required]
        public bool Active { get; set; }
        [Required]
        public int PositionId { get; set; }
        public virtual JobPosition Position { get; set; }
       // [Required]
        public int ShiftId { get; set; }
        public virtual Shift Shift { get; set; }
        //[Required]
        public Contract Contract { get; set; }

        //Safran
        public BusinessUnit BusinessUnit { get; set; }
        
        public int  SupervisorNumber { get; set; }
        [NotMapped]
        public virtual Employee Supervisor { get; set;}
        
        public int ManagerNumber { get; set; }

        [NotMapped]
        public virtual Employee Manager { get; set;}
        

        public int DirectorNumber { get; set; }
        [NotMapped]

        public virtual Employee Director { get; set;}

        float InternSalary { get; set; }
        float Salary { get; set; }

        public bool Direct { get; set; } //1 - Directos 0 - Indirectos
        public bool Hourly { get; set; } //1 - Hourly 0- Salary

        //public virtual ICollection<Evaluation> Evaluations { get; set; }
        [NotMapped]
        public ICollection<Miscellaneous> Miscellaneous { get; set; }

        [DataType(DataType.Date)]
        DateTime DepartureDate { get; set; }

        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public DateTime Created { get; set; } = DateTime.UtcNow;

        [TimestampAttribute ]
        //[DatabaseGenerated(DatabaseGeneratedOption.Computed)]
        public DateTime Updated { get; set; } = DateTime.UtcNow;

        public Employee(){
            Id = Guid.NewGuid();
        }
    }
}