using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Interno.Domain.Catalog
{
    public class Person
    {
        [Key]
        public int Id { get; set; }
        [Required]
        [Display(Name = "Patern Last Name")]
        [MaxLength(25)]
        public string LastNamePat { get; set; } //* */
        [MaxLength(25)]
        [Display(Name = "Matern Last Name")]
        public string LastNameMat { get; set; }//* */
        [Required]
        [MaxLength(25)]
        [Display(Name = "First Name")]
        public string FirstName { get; set; }//* */
        [MaxLength(25)]
        [Display(Name = "Middle Name")]
        public string MiddleName { get; set; }//* */
        [MaxLength(150)]

        public string PrettyName { get; set; }

        [MaxLength(50)]
        public string SSN { get; set; }

        [StringLength(50, ErrorMessage = "Enter Valid RFC."), RegularExpression(@"^([A-ZÑ\x26]{3,4}([0-9]{2})(0[1-9]|1[0-2])(0[1-9]|1[0-9]|2[0-9]|3[0-1]))((-)?([A-Z\d]{3}))?$")]
        public string RFC { get; set; }

        [StringLength(50, ErrorMessage = "Enter Valid CURP."), RegularExpression(@"^([A-Z]{4}([0-9]{2})(0[1-9]|1[0-2])(0[1-9]|1[0-9]|2[0-9]|3[0-1])[HM](AS|BC|BS|CC|CL|CM|CS|CH|DF|DG|GT|GR|HG|JC|MC|MN|MS|NT|NL|OC|PL|QT|QR|SP|SL|SR|TC|TS|TL|VZ|YN|ZS|NE)[A-Z]{3}[0-9A-Z]\d)$")]
        public string CURP { get; set; }

        [Required]
        [DataType(DataType.Date)]
        public DateTime Birthday { get; set; }//* */
        [MaxLength(25)]
        public string Nationality { get; set; }//* */
        [MaxLength(25)]
        public string Birthplace { get; set; }//* */

        //[Required]
        public virtual Gender Gender { get; set; }//* */
        public float Height { get; set; }
        public float Weight { get; set; }

        [Display(Name = "Relationship Status")]
        public virtual RelationshipStatus RelationshipStatus { get; set; } //* */
        public int Childrens { get; set; }

        //public virtual ICollection<Kin> Kin { get; set; } //Parientes only HR

        [Display(Name = "Blood Type")]
        public virtual BloodType BloodType { get; set; }//* */
        [MaxLength(25)]
        public string Religion { get; set; }

        //Miscellaneous
        public bool Passport { get; set; }
        public bool Visa { get; set; }
        public bool Sentry { get; set; }

        [Display(Name = "Global Entry")]
        public bool GlobalEntry { get; set; }
        [Display(Name = "Travel Availability")]
        public bool TravelAvailability { get; set; }
        public bool Relocation { get; set; }

        //Image
        //public FileData Image { get; set; }

        [MaxLength(250)]
        public string AboutMe { get; set; }
        public virtual ICollection<Address> Address { get; set; }
        public virtual ICollection<Phone> Phone { get; set; }
        public virtual ICollection<License> License { get; set; }
        public virtual ICollection<Mail> Mail { get; set; }
        //Contactos de localizacion de la persona
        public virtual ICollection<Contact> Contact { get; set; }

        [Timestamp]
        //[DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public DateTime Created { get; set; } = DateTime.UtcNow;
        //[TimestampAttribute]
        //[DatabaseGenerated(DatabaseGeneratedOption.Computed)]
        //public DateTime Updated { get; set; } = DateTime.UtcNow;

        //public InternoUser UpdateUser { get; set; }
        public bool Suspended { get; set; } //Activo o Suspendido
        public string FullName()
        {
            return FirstName + " " + LastNamePat + " " + LastNameMat;
        }

        [NotMapped]
        public virtual ICollection<Miscellaneous> Miscellaneous { get; set; }
    }

    public enum Gender
    {
        Male = 1,
        Female = 2
    }
    public enum RelationshipStatus
    {
        Unspecified,
        Engaged,
        InAsOpenRelationship,
        InRelationship,
        IsSingle,
        IsComplicated,
        Married
    }
}